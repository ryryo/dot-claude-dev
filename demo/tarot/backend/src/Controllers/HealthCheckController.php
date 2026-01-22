<?php

declare(strict_types=1);

namespace TarotDemo\Controllers;

class HealthCheckController
{
    public function handle(): array
    {
        return ['status' => 'ok'];
    }
}
