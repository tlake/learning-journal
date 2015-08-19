

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
            ajaxSaveNewEntry(event);
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

    var id = $('form').id;
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
    }).done(function(response) {
        ajaxUpdateListView();
        $('#ajax-content').hide();
        $('#primary-content').show();
    }).fail(function() {
        alert('error');
    });
};


var ajaxUpdateListView = function() {
    var url = '/';

    $.ajax({
        method: 'GET',
        url: url
    }).done(function(response) {
        var entry = response.entries[0];
        var id = entry.id;
        var created = moment(entry.created).format('ll');
        var title = entry.title;

        var $li = $('<li class="entry-link"></li>');
        var $a = $('<a href="/detail/' + id + '"></a>');

        $a.append(created + ": " + title);
        $li.append($a);
        $('#toc').prepend($li);
    }).fail(function() {
        alert('error');
    });
};


// event listener to catch button clicks for AJAX requests
$('body').on("click", clickHandler);
