var dt = null;
var parsed = [];

function update_dashboard() {

    $.getJSON( "data/logs.json", function(d) {

        $.each( d.data, function( key, log ) {
            
            if( parsed.indexOf(log.id) < 0 ) {
                new_row = dt.row.add( [ log.type.toUpperCase(), log.text, log.logged ] ).draw().node();
                $(new_row).addClass('log-'+log.type);
                parsed.push(log.id);
            }

        });

        if(d.status == "in_progress") {
            setTimeout(update_dashboard, 2000);
        }
    });
    
}

$(document).ready(function() {
    dt = $('#dataTable').DataTable({
        "columns": [
          { "width": "100px" },
          null,
          { "width": "100px" }
        ] });
    setTimeout(update_dashboard, 500);
});