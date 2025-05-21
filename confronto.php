<?php
$conn = new mysqli("localhost", "usuario", "senha", "jogos.db");
$jogo_id = $_GET['ID'];

$sql = "
    SELECT
        mandante,
        mandante_Placar,
        visitante_Placar,
        visitante
    FROM jogos
    WHERE ID = $jogo_id
";
$result = $conn->query($sql);
$jogo = $result->fetch_assoc();
?>