<?php

declare(strict_types=1);

describe('Example', function () {
    it('passes basic assertion', function () {
        expect(true)->toBeTrue();
    });

    it('performs simple calculation', function () {
        expect(1 + 1)->toBe(2);
    });

    it('validates string operations', function () {
        expect('Hello World')->toContain('World');
    });
});
