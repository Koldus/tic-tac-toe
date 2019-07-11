var dt = null;
var parsed = 0;

function parseLog( i, raw ) {
    var log = { id : i, type : "", text : "", logged : "" };
    console.log(raw);
    raw = raw.split(";");
    
    // Covert raw data to the log object and pass it back
    log.logged = raw[0];
    log.type = raw[1];
    
    log.text = "<span>" + raw[2].replace(".py","") + ":</span> " + raw[3];
    return log;
}

function update_dashboard() {

    // Simplify if additional requests are not required
    $.when(
        $.ajax({ url: "data/main.log", dataType: "text" })
    ).then(
        (main) => {
            main = main.split('\n');
            $.each( main, function( index ) {
                // Ignore empty lines
                if( main[index] != "" ) {
                    // Parse only new logs
                    if(index >= parsed) {
                        log = parseLog( index, main[index] );
                        new_row = dt.row.add( [ log.id, log.type.toUpperCase(), log.text, log.logged ] ).draw().node();
                        $(new_row).addClass('log-'+log.type);
                        parsed += 1;
                    }
                }
            });
            // Set timeout for the next check
            setTimeout(update_dashboard, 2000);
        }, err => { console.log(err); }
    );
    

    // $.getJSON( "data/logs.json", function(d) {

    //     $.each( d.data, function( key, log ) {
            
    //         if( parsed.indexOf(log.id) < 0 ) {
    //             new_row = dt.row.add( [ log.type.toUpperCase(), log.text, log.logged ] ).draw().node();
    //             $(new_row).addClass('log-'+log.type);
    //             parsed.push(log.id);
    //         }

    //     });

    //     if(d.status == "in_progress") {
    //         setTimeout(update_dashboard, 2000);
    //     }
    // });
    
}

$(document).ready(function() {
    dt = $('#dataTable').DataTable({
        "columns": [
            { "width" : "20px" },
            { "width": "100px" },
            null,
            { "width": "180px" }
        ] });
    setTimeout(update_dashboard, 500);
});