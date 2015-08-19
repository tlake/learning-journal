

var clickHandler = function(event) {
    var target = event.target;

    switch(target.id) {
        case 'new-entry-btn':
            newEntry(event);
            break;
        case 'edit-btn':
            editEntry(event);
            break;
        case 'post-entry-btn':
            if ( $('#toc').length ) {
                ajaxSaveNewEntry(event);
            } else {
                ajaxSaveEditEntry(event);
            }
            break;

    }
};


var newEntry = function(event) {
    event.preventDefault();

    $('#primary-content').hide();
    $('#ajax-content').show();
};


var editEntry = function(event) {
    event.preventDefault();

    var url = '/edit/' + $('#edit-btn').data('entry-id');

    $.ajax({
        method: 'GET',
        url: url,
        context: '#ajax-content',
    }).done( function(response) {
        $('#entry-title').val(response.entry.title);
        $('#entry-text').val(response.entry.text);
        $('#primary-content').hide();
        $('#ajax-content').show();
    }).fail( function() {
        alert('error');
    });
};


var ajaxSaveNewEntry = function(event) {
    event.preventDefault();

    var title = $('#entry-title').val();
    var text = $('#entry-text').val();
    var url = '/edit/new';

    $.ajax({
        method: 'POST',
        url: url,
        data: {
            title: title,
            text: text,
        }
    }).done( function(response) {
        ajaxUpdateListView();
        $('#ajax-content').hide();
        $('#primary-content').show();
    }).fail( function() {
        alert('error');
    });
};


var ajaxUpdateListView = function() {
    var url = '/';

    $.ajax({
        method: 'GET',
        url: url
    }).done( function(response) {
        var entry = response.entries[0];
        var id = entry.id;
        var created = moment(entry.created).format('ll');
        var title = entry.title;

        var $li = $('<li class="entry-link"></li>');
        var $a = $('<a href="/detail/' + id + '"></a>');

        $a.append(created + ": " + title);
        $li.append($a);
        $('#toc').prepend($li);
    }).fail( function() {
        alert('error');
    });
};


var ajaxSaveEditEntry = function(event) {
    event.preventDefault();

    var title = $('#entry-title').val();
    var text = $('#entry-text').val();
    var entryID = $('#edit-btn').data('entry-id');
    var url = '/edit/' + entryID;

    $.ajax({
        method: 'POST',
        url: url,
        data: {
            title: title,
            text: text,
        },
    }).done( function(response) {
        ajaxUpdateDetailView(entryID);
        $('#ajax-content').hide();
        $('#primary-content').show();
    }).fail( function() {
        alert('error');
    });
};


var ajaxUpdateDetailView = function(entryID) {
    var url = '/detail/' + entryID;

    $.ajax({
        method: 'GET',
        url: url,
        context: '#ajax-content',
    }).done( function(response) {
        var entry = response.entry;
        var title = entry.title;
        var text = entry.text;

        $('#entry-h1').html(title);
        $('#entry-span').html(text);
    });
};


// event listener to catch button clicks for AJAX requests
$('body').on("click", clickHandler);
