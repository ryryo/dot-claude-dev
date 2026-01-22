<?php

declare(strict_types=1);

require_once __DIR__ . '/../vendor/autoload.php';

use TarotDemo\Router;
use TarotDemo\Controllers\HealthCheckController;

// CORS設定
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json');

// プリフライトリクエストの処理
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$router = new Router();

// ルート定義
$router->get('/api/health', function () {
    $controller = new HealthCheckController();
    $response = $controller->handle();
    echo json_encode($response);
});

// リクエストのディスパッチ
$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

$router->dispatch($method, $path);
