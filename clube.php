<?php
include 'conexao.php';

$clube = $_GET['nome'] ?? '';

echo "<h2>Jogos do clube: " . htmlspecialchars($clube) . "</h2>";

$stmt = $pdo->prepare("
    SELECT * FROM jogos 
    WHERE mandante = ? OR visitante = ?
    ORDER BY rodada
");
$stmt->execute([$clube, $clube]);
$jogos = $stmt->fetchAll(PDO::FETCH_ASSOC);

foreach ($jogos as $jogo) {
    $rodada = $jogo['rodada'];
    $id = $jogo['ID'];
    echo "<p>Rodada $rodada: ";
    echo "{$jogo['mandante']} {$jogo['mandante_Placar']} x {$jogo['visitante_Placar']} {$jogo['visitante']} ";
    echo "<a href='estatisticas.php?id=$id'>(estatísticas)</a>";
    echo "</p>";
}
?>
