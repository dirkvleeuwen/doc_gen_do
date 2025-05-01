document.addEventListener('DOMContentLoaded', function() {
    const select = document.getElementById('id_instrument');
    const dateLabel = document.querySelector('label[for="id_date"]');
    const subjectLabel = document.querySelector('label[for="id_subject"]');
    const considerationsLabel = document.querySelector('label[for="id_considerations"]');
    const requestsRow = document.getElementById('id_requests').closest('.form-row');
  
    function updateLabels() {
      const val = select.value;
      if (val === 'Mondelinge vragen') {
        dateLabel.textContent = 'Datum vergadering';
        requestsRow.style.display = '';
      } else if (val === 'Schriftelijke vragen') {
        dateLabel.textContent = 'Datum indiening';
        requestsRow.style.display = '';
      } else if (val === 'Agendapunt' || val === 'Actualiteit') {
        dateLabel.textContent = 'Datum';
        requestsRow.style.display = 'none';
      } else if (val === 'Motie') {
        dateLabel.textContent = 'Datum vergadering';
        requestsRow.style.display = '';
      } else {
        dateLabel.textContent = 'Datum';
        requestsRow.style.display = '';
      }
      // Pas hier ook subjectLabel en considerationsLabel aan indien gewenst
    }
  
    select.addEventListener('change', updateLabels);
    updateLabels();  // init bij laden
  });