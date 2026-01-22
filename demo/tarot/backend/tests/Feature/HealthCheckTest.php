<?php

declare(strict_types=1);

use TarotDemo\Controllers\HealthCheckController;

describe('HealthCheckController', function () {
    it('returns status ok', function () {
        // Given
        $controller = new HealthCheckController();

        // When
        ob_start();
        $response = $controller->handle();
        $output = ob_get_clean();

        // Then
        expect($response)->toBeArray();
        expect($response)->toHaveKey('status');
        expect($response['status'])->toBe('ok');
    });

    it('returns JSON encodable response', function () {
        // Given
        $controller = new HealthCheckController();

        // When
        $response = $controller->handle();
        $json = json_encode($response);

        // Then
        expect($json)->toBe('{"status":"ok"}');
    });
});
