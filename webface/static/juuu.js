/* juuu.js */

$( document ).ready(function() {

    $(".bar").mouseenter(function() {
        $(this).css("height", 7 + Math.floor(Math.random() * 123)+"px");
    })

    $('label:contains("On")').css("border-color", "blue");
    $('label:contains("Teach")').css("border-color", "magenta");
    $('label:contains("Off")').css("border-color", "red");

    $('#full').click(function() {
        $('input[value="full"]').prop("checked", true);
    })

    $('#on').click(function() {
        $('input[value="on"]').prop("checked", true);
    })

    $('#teach').click(function() {
        $('input[value="teach"]').prop("checked", true);
    })

    $('#off').click(function() {
        $('input[value="off"]').prop("checked", true);
    })

    $("#goo").click(function() {
        $("#submit-1").click();
    });

    $("#topclick").click(function() {
        $('html, body').animate({
            scrollTop: $("nav").offset().top
        }, 777);
    });
    $("#botomclick").click(function() {
        $('html, body').animate({
            scrollTop: $("#conf").offset().top
        }, 777);
    });


    var nav = $('#nav');
    //var navpos = nav.position().top;

    $(window).scroll(function() {
        scrool_pos = $(window).scrollTop();
        if (navpos - scrool_pos > 5) {
            pos = navpos - scrool_pos;
        } else {
            pos = 5;
        }
        $('#nav').css({top: pos});
    })

});

