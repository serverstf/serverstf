module.exports = function(grunt) {
    grunt.initConfig({
        less: {
            default: {
                options: {
                    paths: [
                        "./client/styles/",
                        "./client/external/semantic.gs/stylesheets/less/",
                    ],
                    yuicompress: true
                },
                files: {
                    "./client/styles/client.css":
                        "./client/styles/client.less",
                }
            }
        },
        watch: {
            files: "./client/styles/*.less",
            tasks: ["less"]
        }
    });
    grunt.loadNpmTasks("grunt-contrib-less");
    grunt.loadNpmTasks("grunt-contrib-watch");
};
