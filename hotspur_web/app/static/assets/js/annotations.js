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
        }

        // Perfoms synchronization cycle: Send user to server, copy to limbo, update server when done
        function sync_annot() {
                if (Object.keys(user_annotation).length() > 0) {
                        // Set put request
                        // add user to limbo
                        // empty user

                        //success callback (delete limbo/replace server annot with new from server)
                        merge_annot();
                }

        }

        // Initially loads annotation from server
        function load_annotation(callback) {
                d3.json("user_annotation", function (annotation) {
                        my.server_annotation = annotation;
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
        my.annotation = glob_annotation;

        return(my);
}());