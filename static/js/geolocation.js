// ============================================================
// GÉOLOCALISATION
// ============================================================

const GEOLOCATION_CONFIG = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 0
};

function getLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject('La géolocalisation n\'est pas supportée par votre navigateur');
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                });
            },
            (error) => {
                let message = 'Erreur de géolocalisation';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        message = '❌ Vous devez autoriser la géolocalisation pour pointer';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message = '❌ Position non disponible';
                        break;
                    case error.TIMEOUT:
                        message = '❌ Délai de géolocalisation dépassé';
                        break;
                }
                reject(message);
            },
            GEOLOCATION_CONFIG
        );
    });
}

function verifierZoneEntreprise(lat, lng) {
    // Coordonnées de l'entreprise (à configurer selon votre emplacement)
    const entrepriseLat = 6.3600;   // Latitude de votre entreprise
    const entrepriseLng = 2.4150;   // Longitude de votre entreprise
    const rayon = 0.005;            // Rayon en degrés (environ 500m)
    
    const distance = Math.sqrt(
        Math.pow(lat - entrepriseLat, 2) + 
        Math.pow(lng - entrepriseLng, 2)
    );
    
    return distance <= rayon;
}

function afficherMessage(message, type) {
    const container = document.getElementById('message-container');
    if (!container) return;
    
    const div = document.createElement('div');
    div.className = `alert alert-${type}`;
    div.textContent = message;
    container.appendChild(div);
    
    setTimeout(() => {
        div.style.opacity = '0';
        div.style.transition = 'opacity 0.5s';
        setTimeout(() => div.remove(), 500);
    }, 5000);
}