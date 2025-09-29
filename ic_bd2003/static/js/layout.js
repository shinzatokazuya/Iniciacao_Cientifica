const inputNav = document.querySelector('#clube_nav');
const autocompleteListNav = document.querySelector('#autocomplete-list-nav');

if (inputNav && autocompleteListNav && typeof window.ALL_CLUBS !== 'undefined') {

    // Função para atualizar a lista
    function updateAutocompleteList(query = '') {
        let html = '';
        let filteredClubs = window.ALL_CLUBS;

        if (query.length > 0) {
            filteredClubs = window.ALL_CLUBS.filter(club => club.toLowerCase().startsWith(query.toLowerCase()));
        }

        for (let club of filteredClubs) {
            html += `<li onclick="selectClubNav('${club.replace(/'/g, "\\'")}')">${club}</li>`;
        }

        autocompleteListNav.innerHTML = html;
        autocompleteListNav.style.display = html ? 'block' : 'none';
    }

    inputNav.addEventListener('keyup', () => {
        let query = inputNav.value.toLowerCase();
        let html = '';
        if (query.length > 0) {
            const filteredClubs = window.ALL_CLUBS.filter(club => club.toLowerCase().startsWith(query));

            if (filteredClubs.length > 0) {
                for (let club of filteredClubs) {
                    html += `<li onclick="selectClubNav('${club.replace(/'/g, "\\'")}')">${club}</li>`;
                }
            }
        }
        autocompleteListNav.innerHTML = html;
        autocompleteListNav.style.display = html ? 'block' : 'none';
    });

    function selectClubNav(clubName) {
        inputNav.value = clubName;
        autocompleteListNav.innerHTML = '';
        autocompleteListNav.style.display = 'none';
    }

    document.addEventListener('click', (event) => {
        if (!event.target.closest('.navbar-search .autocomplete-container')) {
            autocompleteListNav.style.display = 'none';
        }
    });
}
