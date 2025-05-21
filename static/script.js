function buscar() {
    const time = document.getElementById('time').value;

    fetch(`/buscar?time=${encodeURIComponent(time)}`)
        .then(res => res.json())
        .then(data => {
            preencherTabela('estatisticas', ['rodada', 'chutes', 'No Alvo', 'Posse', 'Passes', 'Precisão', 'Faltas', 'Amarelos', 'Vermelhos', 'Impedimentos', 'Escanteios'], data.estatisticas);
            preencherTabela('gols', ['Rodada', 'Atleta', 'Minuto', 'Tipo'], data.gols);
            preencherTabela('cartoes', ['Rodada', 'Atleta', 'Cartão', 'Minuto'], data.cartoes);
        });
}

function preencherTabela(id, colunas, dados) {
    const tabela = document.getElementById(id);
    const thead = tabela.querySelector('thead');
    const tbody = tabela.querySelector('tbody');

    // Cabeçalho
    thead.innerHTML = '<tr>' + colunas.map(c => `<th>${c}</th>`).join('') + '</tr>';

    // Dados
    tbody.innerHTML = '';
    if (dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="' + colunas.length + '">Sem dados</td></tr>';
        return;
    }

    dados.forEach(linha => {
        const tr = document.createElement('tr');
        linha.forEach(celula => {
            const td = document.createElement('td');
            td.textContent = celula;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}
