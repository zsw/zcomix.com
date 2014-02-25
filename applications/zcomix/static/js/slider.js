(function () {
    "use strict";

    function show_slide(num) {
        $('#reader_page .slide').hide();
        var h = $('#img-' + num).children('img')[0].height;
        $('#reader_page #container').height(h);
        $('#reader_page .nav').height(h);
        $('#reader_page .nav').css({'line-height': h + 'px'});
        var w = $('#img-' + num).children('img')[0].width;
        $('#reader_page #container').width(w);
        $('#reader_page .nav-dot').removeClass('current');
        $('#reader_page #img-dot-' + num).addClass('current');
        $('#reader_page #img-' + num).css( "display", "inline-block")
    }

    $(document).ready(function(){
        $('.carousel').carousel();
        var max_image = $('#reader_page .slide').length - 1;
        $('#reader_page .slide').click(function(e) {
            $('#reader_page .slide:visible').each( function(id, elem) {
                var num = $(this).attr('id').split('-')[1];
                num++;
                if (num > max_image) {num = 0;};
                show_slide(num);
            });
        });
        $('#reader_page .nav-dot').click(function(e) {
            var num = $(this).attr('id').split('-')[2];
            show_slide(num);
        });
        setTimeout(function() {
            show_slide(0);
        }.bind(this), 1000);
    });

}());
