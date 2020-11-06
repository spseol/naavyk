
$( document ).ready(function() {

    responseProcess = function(data) {
        alert(data);
    }

    updateClick = function(event) {
        event.preventDefault();
        //$(this).parents('ul').css('color', 'red');
        form = $(this).parents('form');
        //alert(form[0].tagName)
        var fdata = new FormData(form[0]);
        //fdata['gid'] = '{{ gid }}';
        //alert(fdata);
        var url = "{{ url_for('orderAJAX', gid=gid) }}";
        $.ajax({
            url: url,
            data: fdata,
            cache: false,
            processData: false,
            contentType: false,
            type: 'POST',
            success: function (confirmdata) {
                var input = $(form).find('input.count');
                input.val(confirmdata.count);
                $('#total-price').text(confirmdata.price+',-');
                $('#total-count').text(confirmdata.totalcount);
                input.parent().append('<span id="donedone" >&#128504;</span>')
                $('#donedone').fadeOut(800);
                setTimeout(function() {
                    $('#donedone').remove();
                }, 801);

            }
        });
    };

    $('.update').click(updateClick);

});

