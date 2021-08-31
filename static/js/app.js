/*global $ */
$(document).ready(function () { });

var moves = [];

$('#tracks').sortable({
    group: 'list',
    animation: 200,
    ghostClass: 'ghost',
    onEnd: function (evt) {
        if (evt.oldIndex != evt.newIndex) {
            var move = evt.oldIndex + "-" + evt.newIndex;
            console.log(move);
            moves.push(move);
        }
    }
});


// Arrays of "data-id"
$('#get-order').click(function () {
    if (moves.length == 0) {
        console.log("No moves");
        return;
    }
    else {
        // Temporary solution
        // moves.push(document.getElementById("plname").getAttribute("data"));
        var sort1 = $('#tracks').sortable('toArray');
        console.log(sort1);
        $.ajax({
            url: "/change_order",
            type: "POST",
            data: { moves: moves,
                    playlist: $('table').attr('id'),
            },
            success: function (response) {
                $('#error').hide();
                $('#success').show();
            },
            error: function (xhr) {
                console.error(xhr);
                $('#success').hide();
                $('#error').show();
            }
        }).done(() => { location.reload();});
    }
});