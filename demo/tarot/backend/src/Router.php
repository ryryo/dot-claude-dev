<?php

declare(strict_types=1);

namespace TarotDemo;

class Router
{
    private array $routes = [];

    public function get(string $path, callable $handler): void
    {
        $this->addRoute('GET', $path, $handler);
    }

    public function post(string $path, callable $handler): void
    {
        $this->addRoute('POST', $path, $handler);
    }

    private function addRoute(string $method, string $path, callable $handler): void
    {
        $this->routes[$method][$path] = $handler;
    }

    public function dispatch(string $method, string $path): void
    {
        if (!isset($this->routes[$method][$path])) {
            http_response_code(404);
            echo json_encode(['error' => 'Not Found']);
            return;
        }

        $handler = $this->routes[$method][$path];
        $handler();
    }
}
