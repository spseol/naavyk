/* juuu.js */

$( document ).ready(function() {

    $(".bar").mouseenter(function() {
        $(this).css("height", 7 + Math.floor(Math.random() * 123)+"px");
    })

    // Intensify all images with the 'intense' classname.
    //var elements = document.querySelectorAll( 'img' );
	//Intense( elements );

    mediumZoom('.zoomable');

});

