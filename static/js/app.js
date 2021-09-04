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

// Pause other audio when playing a new one
window.addEventListener("play", function (evt) {
    console.log(evt);
    if (window.$_currentlyPlaying && window.$_currentlyPlaying != evt.target) {
        window.$_currentlyPlaying.pause();
    }
    window.$_currentlyPlaying = evt.target;
}, true);

var [SECRET1, SECRET2] = atob(atob("VjJFZ2NHeGhlV3hwYzNRZ2JXZGxaSEpoSUdocFlTQXpibVJySUdFZ0xTQjBjbUZqYTNNc0lHaHNhM1JwSUd4cGJtRWdjMlZ5ZG1WMWNpQWhJU0U9")).split('-');
$('#get-order').click(function () {
    if (moves.length == 0) {
        console.log("No moves");
        return;
    }
    else {
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