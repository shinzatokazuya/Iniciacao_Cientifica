<?php
include 'conexao.php';

// Buscar todas as rodadas disponíveis
$stmtRodadas = $pdo->query("SELECT DISTINCT rodada FROM jogos ORDER BY rodada ASC");
$rodadas = $stmtRodadas->fetchAll(PDO::FETCH_ASSOC);

foreach ($rodadas as $r) {
    $rodada = $r['rodada'];
    echo "<h2>Rodada $rodada</h2>";

    // Buscar jogos da rodada
    $stmt = $pdo->prepare("SELECT * FROM jogos WHERE rodada = ? ORDER BY data, hora");
    $stmt->execute([$rodada]);
    $jogos = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo "<ul>";
    foreach ($jogos as $jogo) {
        $id = $jogo['ID'];
        $mandante = htmlspecialchars($jogo['mandante']);
        $visitante = htmlspecialchars($jogo['visitante']);
        $placar = "{$jogo['mandante_Placar']} x {$jogo['visitante_Placar']}";
        
        echo "<li>";
        echo "<a href='clube.php?nome=" . urlencode($mandante) . "'>$mandante</a> ";
        echo "<strong><a href='estatisticas.php?id=$id'>$placar</a></strong> ";
        echo "<a href='clube.php?nome=" . urlencode($visitante) . "'>$visitante</a>";
        echo "</li>";
    }
    echo "</ul>";
}
?>
