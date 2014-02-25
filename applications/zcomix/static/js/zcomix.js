(function () {
    "use strict";

    $(document).ready(function(){
        setTimeout(function() {
            $('.fixme').click(function(e) {
                alert('This feature is not working yet.');
                e.preventDefault();
            });
        }.bind(this), 1000);
    });

}());
