export function getPlanDirectoryPath(filePath: string): string {
  if (filePath.endsWith('/spec.md')) {
    return filePath.slice(0, -'/spec.md'.length);
  }
  if (filePath.endsWith('/tasks.json')) {
    return filePath.slice(0, -'/tasks.json'.length);
  }
  if (filePath.endsWith('.md')) {
    return filePath.slice(0, -'.md'.length);
  }
  return filePath;
}
