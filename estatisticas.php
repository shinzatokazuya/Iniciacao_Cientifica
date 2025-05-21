<?php
include 'conexao.php';

$partida_id = $_GET['id'] ?? 0;

// Buscar dados da partida
$stmt = $pdo->prepare("SELECT * FROM jogos WHERE ID = ?");
$stmt->execute([$partida_id]);
$jogo = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$jogo) {
    echo "Partida não encontrada.";
    exit;
}

echo "<h2>Estatísticas da partida</h2>";
echo "<p>{$jogo['mandante']} {$jogo['mandante_Placar']} x {$jogo['visitante_Placar']} {$jogo['visitante']}</p>";

// Buscar estatísticas
$stmt = $pdo->prepare("SELECT * FROM estatisticas WHERE partida_id = ?");
$stmt->execute([$partida_id]);
$estatisticas = $stmt->fetchAll(PDO::FETCH_ASSOC);

foreach ($estatisticas as $e) {
    echo "<h3>" . htmlspecialchars($e['clube']) . "</h3>";
    echo "<ul>";
    echo "<li>Chutes: {$e['chutes']}</li>";
    echo "<li>Chutes no alvo: {$e['chutes_no_alvo']}</li>";
    echo "<li>Posse de bola: {$e['posse_de_bola']}</li>";
    echo "<li>Passes: {$e['passes']}</li>";
    echo "<li>Precisão dos passes: {$e['precisao_passes']}</li>";
    echo "<li>Faltas: {$e['faltas']}</li>";
    echo "<li>Amarelos: {$e['cartao_amarelo']}</li>";
    echo "<li>Vermelhos: {$e['cartao_vermelho']}</li>";
    echo "<li>Impedimentos: {$e['impedimentos']}</li>";
    echo "<li>Escanteios: {$e['escanteios']}</li>";
    echo "</ul>";
}
?>
