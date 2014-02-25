(function () {
    "use strict";

    $(document).ready(function(){
        $('#contribute_link').click( function(e) {
            var amount = $('#contribute_amount').val();
            var href = $('#contribute_link').attr('href');
            window.open(href + '?amount=' + amount.toString());
            e.preventDefault();
        });
    });

}());
