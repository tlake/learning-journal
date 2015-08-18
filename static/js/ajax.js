

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
            ajaxSaveEntry(event);
            break;

    }
};


var newEntry = function(event) {
    event.preventDefault();

    $('#list-guts').hide();
    $('#edit-guts').show();
};


var editEntry = function(event) {
    event.preventDefault();
};

var ajaxSaveEntry = function(event) {
    event.preventDefault();
    var title = $('#entry-title').val();
    var text = $('#entry-text').val();
    var url = '/edit/new';

    console.log(title);
    console.log(text);

    $.ajax({
        method: 'POST',
        url: url,
        data: {
            title: title,
            text: text,
        }
    }).done(function(response) {
        $('#edit-guts').hide();
        $('#list-guts').show();
    }).fail(function() {
        alert('error');
    });
};


// event listener to catch button clicks for AJAX requests
$('body').on("click", clickHandler);
