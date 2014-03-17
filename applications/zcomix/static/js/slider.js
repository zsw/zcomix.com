(function () {
    "use strict";

    function show_slide(num) {
        $('#reader_section .slide').hide();
        var h = $('#img-' + num).children('img')[0].height;
        $('#reader_section #container').height(h);
        $('#reader_section .nav').height(h);
        $('#reader_section .nav').css({'line-height': h + 'px'});
        var w = $('#img-' + num).children('img')[0].width;
        $('#reader_section #container').width(w);
        $('#reader_section .nav-dot').removeClass('current');
        $('#reader_section #img-dot-' + num).addClass('current');
        $('#reader_section #img-' + num).css( "display", "inline-block")
    }

    $(document).ready(function(){
        $('.carousel').carousel();
        var max_image = $('#reader_section .slide').length - 1;
        $('#reader_section .slide').click(function(e) {
            $('#reader_section .slide:visible').each( function(id, elem) {
                var num = $(this).attr('id').split('-')[1];
                num++;
                if (num > max_image) {num = 0;};
                show_slide(num);
            });
        });
        $('#reader_section .nav-dot').click(function(e) {
            var num = $(this).attr('id').split('-')[2];
            show_slide(num);
        });
        setTimeout(function() {
            show_slide(0);
        }.bind(this), 1000);
    });

}());
