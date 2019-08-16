var dt = null;
var parsed = 0;

function parseLog( i, raw ) {
    var log = { id : i, type : "", text : "", logged : "" };
    
    raw = raw.split(";");
    
    // Covert raw data to the log object and pass it back
    log.logged = raw[0];
    log.type = raw[1];
    
    log.text = "<span>" + raw[2].replace(".py","") + ":</span> " + raw[3];
    return log;
}

function update_dashboard() {
    console.log("i\'m here")
    // Simplify if additional requests are not required
    $.when(
        $.ajax({ url: "data/main.log", dataType: "text" })
    ).then(
        (main) => {
            console.log(main)
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
            $('#status_img_1').attr("src", "data/raw_image.jpg?" + new Date().getTime() );
            $('#status_img_2').attr("src", "data/lines.jpg?" + new Date().getTime() );
            $('#status_img_3').attr("src", "data/current_state_raw.jpg?" + new Date().getTime() );
            $('#status_img_4').attr("src", "data/game_state.jpg?" + new Date().getTime() );
            
        }, err => { console.log(err); },
        // Set timeout for the next check
        setTimeout(update_dashboard, 2000)
    );
    
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