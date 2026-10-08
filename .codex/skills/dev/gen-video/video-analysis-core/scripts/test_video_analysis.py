import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import video_analysis as v


def data(values):
    values = np.asarray(values, dtype=np.float32)
    return {'x': np.repeat(values[:, None], 768, axis=1),
            'z': np.repeat(values[:, None], 256, axis=1),
            'h': np.zeros((len(values), 48)), 'quality': np.ones(len(values)),
            'contrast': np.ones(len(values))*.2,
            'delta': np.r_[0, np.abs(np.diff(values))],
            'ts': np.arange(len(values))/24}


class SelectionTests(unittest.TestCase):
    def test_short_nontext_event_survives_candidate_selection(self):
        d = data([.1]*30 + [.8]*4 + [.1]*30)
        segments = v.build_segments(d)
        self.assertTrue(any(30 <= i < 34 for s in segments for i in s['candidate_indices']))

    def test_unasked_change_then_similar_pose_is_not_repeated(self):
        d = data([0, .8, .79, .02])
        segments = [{'id': 0, 'candidate_indices': [0, 1, 2, 3]}]
        chosen = v.supplemental(d, segments, {0}, 4, .08)
        self.assertEqual([r['frame_index'] for r in chosen], [1])
        self.assertEqual(v.supplemental(d, segments, {0, 1}, 4, .08), [])

    def test_unrepresented_segment_receives_coverage_within_budget(self):
        d = data([0, .1, .2])
        segments = [{'id': 0, 'candidate_indices': [0, 1]}, {'id': 1, 'candidate_indices': [2]}]
        chosen = v.supplemental(d, segments, {0}, 1, .08)
        self.assertEqual(chosen[0]['frame_index'], 2)
        self.assertEqual(chosen[0]['reason'], 'unrepresented_segment')

    def test_sequence_frame_covers_a_candidate_even_if_not_in_catalog(self):
        d = data([0, .8, .79])
        segments = [{'id': 0, 'start_frame': 0, 'end_frame_exclusive': 3,
                     'candidate_indices': [0, 1]}]
        self.assertEqual(v.supplemental(d, segments, {0, 2}, 4, .08), [])

    def test_flat_video_still_has_a_representative(self):
        segments = v.build_segments(data([0]*20))
        self.assertGreaterEqual(sum(len(s['candidate_indices']) for s in segments), 1)


class CliTests(unittest.TestCase):
    def test_arbitrary_source_timestamps_sequence_and_concurrent_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root/'arbitrary name.mkv'
            colors = [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255)]
            frames = b''.join(bytes(c)*64*48 for c in colors for _ in range(4))
            subprocess.run(['ffmpeg','-v','error','-f','rawvideo','-pix_fmt','rgb24',
                            '-s','64x48','-r','8','-i','-','-c:v','ffv1',str(source)],
                           input=frames,check=True)
            script = str(Path(v.__file__).resolve())
            cmd = [sys.executable,script]
            def run(*args):
                return json.loads(subprocess.check_output(cmd+list(args)))
            session = root/'session'
            initial = run('prepare',str(source),'--out',str(session),'--max-initial','1','--extra-budget','2')
            self.assertEqual(initial['decoded_frames'],20)
            self.assertEqual(len(initial['frames']),1)
            self.assertGreater(initial['initial_cap_omitted_segments'],0)
            jobs=[subprocess.Popen(cmd+['supplement',str(session),'--count','1','--reason','coverage'],
                                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(4)]
            outcomes=[(job,job.communicate()) for job in jobs]
            good=[json.loads(out[0]) for job,out in outcomes if job.returncode==0]
            self.assertEqual(len(good),2)
            ids=[f['frame_index'] for result in good for f in result['frames']]
            self.assertEqual(len(set(ids)),2)
            self.assertNotIn(initial['frames'][0]['frame_index'],ids)
            state=json.loads((session/'state.json').read_text())
            self.assertEqual(sum(len(r['frames']) for r in state['requests']),2)
            for result in good:
                for f in result['frames']:
                    self.assertTrue(Path(f['path']).is_file())
                    self.assertAlmostEqual(f['seconds'],f['frame_index']/8)
            # A separate session tests sequence sampling disclosure without reusing the budget.
            second=root/'sequence'
            run('prepare',str(source),'--out',str(second),'--max-initial','1','--extra-budget','2')
            seq=run('sequence',str(second),'--start','0','--end','.5','--count','8','--reason','motion')
            self.assertEqual(len(seq['frames']),2)
            self.assertFalse(seq['all_source_frames_included'])
            self.assertEqual([f['seconds'] for f in seq['frames']],[0.,.5])

if __name__ == '__main__':
    unittest.main()
