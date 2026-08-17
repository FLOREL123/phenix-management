// ============================================================
// FONCTIONS PRINCIPALES
// ============================================================

async function pointer(type) {
    const btn = document.querySelector(`#btn-${type}`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> En cours...';
    }
    
    try {
        // Récupérer la position
        const position = await getLocation();
        
        // Vérifier que le stagiaire est dans la zone
        if (!verifierZoneEntreprise(position.latitude, position.longitude)) {
            afficherMessage('❌ Vous devez être dans l\'entreprise pour pointer', 'danger');
            resetButton(btn);
            return;
        }
        
        // Envoyer la requête
        const response = await fetch('/api/pointer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: type,
                latitude: position.latitude,
                longitude: position.longitude
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            afficherMessage(`✅ ${data.message}`, 'success');
            setTimeout(() => window.location.reload(), 1500);
        } else {
            afficherMessage(`❌ ${data.message}`, 'danger');
            resetButton(btn);
        }
        
    } catch (error) {
        afficherMessage(`❌ ${error}`, 'danger');
        resetButton(btn);
    }
}

function resetButton(btn) {
    if (btn) {
        btn.disabled = false;
        if (btn.id === 'btn-arrivee') {
            btn.innerHTML = '✅ Arrivée';
        } else if (btn.id === 'btn-depart') {
            btn.innerHTML = '🚪 Départ';
        }
    }
}

// ============================================================
// HISTORIQUE - CHARGEMENT INFINI
// ============================================================

let page = 1;
let loading = false;
let hasMore = true;

function chargerHistorique() {
    if (loading || !hasMore) return;
    
    loading = true;
    document.getElementById('loader').style.display = 'block';
    
    fetch(`/api/historique?page=${page}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('historique-container');
            
            data.pointages.forEach(p => {
                const div = document.createElement('div');
                div.className = 'historique-item';
                div.innerHTML = `
                    <div class="date">${p.date}</div>
                    <div class="heures">
                        <span>Arrivée: ${p.heure_arrivee || '-'}</span>
                        <span>Départ: ${p.heure_depart || '-'}</span>
                    </div>
                    <span class="badge badge-${p.statut === 'Présent' ? 'success' : 'danger'}">${p.statut}</span>
                `;
                container.appendChild(div);
            });
            
            hasMore = data.has_more;
            page++;
            loading = false;
            document.getElementById('loader').style.display = 'none';
        })
        .catch(() => {
            loading = false;
            document.getElementById('loader').style.display = 'none';
        });
}

// Scroll infini
if (document.getElementById('historique-container')) {
    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
            chargerHistorique();
        }
    });
}