HOTSPUR_ANNOTATION = (function () {
        my = {};
        // Holds all annotations
        var glob_annotation = {};
        // Holds annotations made by user
        var user_annotation = {};
        // Holds annotations sent to server while waiting for response
        var limbo_annotation = {};
        // Holds annotations loaded from server
        var server_annotation = {};


        // Creates Global annotation list from all three annotation objects
        function merge_annot() {
                glob_annotation = {};
                for (var micrograph in server_annotation) {
                        glob_annotation[micrograph] = server_annotation[micrograph];
                }
                for (var micrograph in limbo_annotation) {
                        glob_annotation[micrograph] = limbo_annotation[micrograph];
                }
                for (var micrograph in user_annotation) {
                        glob_annotation[micrograph] = user_annotation[micrograph];
                }
                my.annotation = glob_annotation;
        }

        // Perfoms synchronization cycle: Send user to server, copy to limbo, update server when done
        function sync_annot() {
                if (Object.keys(user_annotation).length > 0) {
                        // Set put request
                        $.ajax({
                                type: 'POST',
                                url: 'user_annotation',
                                data: JSON.stringify(user_annotation),
                                contentType: 'application/json;charset=UTF-8',
                                dataType: 'html',
                                success: function (responseData, textStatus, jqXHR) {
                                        limbo_annotation = {};
                                        server_annotation = JSON.parse(responseData)['user_annotation'];
                                        merge_annot();
                                        my.annotation = glob_annotation;
                                },
                                error: function (responseData, textStatus, errorThrown) {
                                        alert('Error: ' + errorThrown + ". Status: " + textStatus);
                                }
                        });
                        // add user to limbo
                        for (var micrograph in user_annotation) {
                        limbo_annotation[micrograph] = user_annotation[micrograph];
                        }
                        // empty user
                        user_annotation = {};

                        //success callback (delete limbo/replace server annot with new from server)
                        merge_annot();
                }

        }
        setInterval(function(){ 
                console.log("Syncing");
                console.log([glob_annotation,server_annotation,user_annotation,limbo_annotation]);
                sync_annot(); 
                console.log("Synced");
                console.log([glob_annotation,server_annotation,user_annotation,limbo_annotation])}, 30000);

        // Initially loads annotation from server
        function load_annotation(callback) {
                d3.json("user_annotation", function (annotation) {
                        server_annotation = annotation['user_annotation'];
                        merge_annot();
                        
                        callback(my);
                });
        }

        // Performs an annotation
        function annotate(micrograph, annotation_func) {
                if (!user_annotation[micrograph]) {
                        user_annotation[micrograph] = {};
                }
                annotation_func(user_annotation[micrograph]);
                merge_annot();

        }

        my.load_annotation = load_annotation;
        my.annotate = annotate;
        my.annotation = glob_annotation;

        return (my);
}());