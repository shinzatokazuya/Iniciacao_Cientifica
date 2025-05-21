<?php
try {
    $pdo = new PDO("sqlite:jogos.db");
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("ERRO na conexão: ". $e->getMessage());
}
?>
