document.addEventListener('DOMContentLoaded', function() {
  // Share-button functionality
  var shareBtn = document.getElementById('shareButton');
  if (shareBtn && navigator.share) {
    var offcanvas = document.getElementById('offcanvasPreview');
    var shareText = offcanvas ? offcanvas.querySelector('pre').textContent.trim() : '';
    shareBtn.addEventListener('click', function() {
      navigator.share({
        title: document.title,
        text: shareText
      }).catch(function(error) {
        console.error('Error sharing:', error);
      });
    });
  } else if (shareBtn) {
    shareBtn.style.display = 'none';
  }

  // Dynamic submitter formset
  var addBtn = document.getElementById('add-submitter');
  var container = document.getElementById('submitters-container');
  var totalFormsInput = document.querySelector('input[name$="-TOTAL_FORMS"]');
  var emptyTemplate = document.getElementById('empty-form-template');
  if (addBtn && container && totalFormsInput && emptyTemplate) {
    addBtn.addEventListener('click', function() {
      var currentCount = parseInt(totalFormsInput.value, 10);
      var newFormHtml = emptyTemplate.innerHTML.replace(/__prefix__/g, currentCount);
      var tempDiv = document.createElement('div');
      tempDiv.innerHTML = newFormHtml;
      var newForm = tempDiv.firstElementChild;
      var counter = newForm.querySelector('.submitter-counter-text');
      if (counter) {
        counter.textContent = 'Indiener ' + (currentCount + 1);
      }
      container.appendChild(newForm);
      totalFormsInput.value = currentCount + 1;
    });
  }

  // Dynamic title update
  var instrumentSelect = document.getElementById('id_instrument');
  var subjectInput = document.getElementById('id_subject');
  var dateInput = document.getElementById('id_date');
  var titleSpan = document.getElementById('form-title');
  if (instrumentSelect && subjectInput && dateInput && titleSpan) {
    function formatDate(value) {
      var months = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december'];
      var parts = value.split('-');
      if (parts.length === 3) {
        var d = parseInt(parts[2], 10);
        var m = parseInt(parts[1], 10);
        return d + ' ' + months[m-1] + ' ' + parts[0];
      }
      return value;
    }
    function updateTitle() {
      var instrText = instrumentSelect.options[instrumentSelect.selectedIndex].text || '';
      var dateVal = dateInput.value ? formatDate(dateInput.value) : '';
      var subj = subjectInput.value || '';
      var text = '';
      if (instrText && dateVal && subj) {
        text = instrText + (instrText === 'Schriftelijke vragen' ? ' van ' : ' voor de vergadering van ') + dateVal + ' inzake ' + subj;
      } else if (instrText && dateVal) {
        text = instrText + (instrText === 'Schriftelijke vragen' ? ' van ' : ' voor de vergadering van ') + dateVal;
      } else if (instrText && subj) {
        text = instrText + ' inzake ' + subj;
      } else if (dateVal && subj) {
        text = (instrText === 'Schriftelijke vragen' ? 'van ' : 'voor de vergadering van ') + dateVal + ' inzake ' + subj;
      } else {
        text = instrText || dateVal || (subj ? 'inzake ' + subj : '');
      }
      titleSpan.textContent = text;
    }
    instrumentSelect.addEventListener('change', updateTitle);
    dateInput.addEventListener('input', updateTitle);
    subjectInput.addEventListener('input', updateTitle);
    updateTitle();
  }

  // Auto-resize textareas
  document.querySelectorAll('.auto-resize-textarea').forEach(function(textarea) {
    function resize() {
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    }
    textarea.addEventListener('input', resize);
    resize();
  });

  // Notes AJAX helpers
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      document.cookie.split(';').forEach(function(cookie) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        }
      });
    }
    return cookieValue;
  }
  var csrftoken = getCookie('csrftoken');

  // Add note via AJAX
  var noteForm = document.getElementById('note-form');
  if (noteForm) {
    noteForm.addEventListener('submit', function(e) {
      e.preventDefault();
      fetch(noteForm.action, {
        method: 'POST',
        headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrftoken},
        body: new FormData(noteForm)
      })
      .then(response => response.json())
      .then(json => {
        if (json.notes_html) {
          document.getElementById('notes-list').innerHTML = json.notes_html;
          noteForm.reset();
        }
      })
      .catch(console.error);
    });
  }

  // Delete and edit notes
  var notesList = document.getElementById('notes-list');
  if (notesList) {
    notesList.addEventListener('click', function(e) {
      var deleteBtn = e.target.closest('.js-delete-note');
      if (deleteBtn) {
        e.preventDefault();
        if (!confirm('Weet je zeker dat je deze notitie wilt verwijderen?')) return;
        fetch(deleteBtn.dataset.url, {
          method: 'POST',
          headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrftoken}
        })
        .then(res => res.json())
        .then(json => {
          if (json.notes_html) notesList.innerHTML = json.notes_html;
        })
        .catch(console.error);
        return;
      }
      var editBtn = e.target.closest('.js-edit-note');
      if (editBtn) {
        e.preventDefault();
        var noteItem = editBtn.closest('li');
        var textElem = noteItem.querySelector('p.mb-1');
        var originalText = textElem.innerText;
        var textarea = document.createElement('textarea');
        textarea.className = 'form-control form-control-sm mb-2';
        textarea.value = originalText;
        textElem.replaceWith(textarea);
        var actionBtns = noteItem.querySelector('.text-nowrap');
        if (actionBtns) actionBtns.style.display = 'none';
        var saveBtn = document.createElement('button');
        saveBtn.type = 'button';
        saveBtn.className = 'btn btn-sm btn-outline-primary me-1';
        saveBtn.textContent = 'Opslaan';
        var cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.className = 'btn btn-sm btn-outline-secondary';
        cancelBtn.textContent = 'Annuleren';
        var btnWrapper = document.createElement('div');
        btnWrapper.className = 'mt-2';
        btnWrapper.append(saveBtn, cancelBtn);
        textarea.after(btnWrapper);
        cancelBtn.addEventListener('click', function() {
          btnWrapper.remove();
          textarea.replaceWith(textElem);
          if (actionBtns) actionBtns.style.display = '';
        });
        saveBtn.addEventListener('click', function() {
          var data = new FormData();
          data.append('text', textarea.value);
          fetch(editBtn.dataset.url, {
            method: 'POST',
            headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrftoken},
            body: data
          })
          .then(res => res.json())
          .then(json => {
            if (json.notes_html) notesList.innerHTML = json.notes_html;
          })
          .catch(console.error);
        });
      }
    });
  }
});