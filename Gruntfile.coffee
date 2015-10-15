module.exports = (grunt) ->
    grunt.initConfig(
        watch:
            stylesheets:
                files: ["serverstf/ui/styles/*.less"]
                tasks: ["clean:stylesheets", "less"]
            scripts:
                files: ["serverstf/ui/lib/**/*.coffee"]
                tasks: ["clean:coffee", "coffee"]
        less:
            default:
                options:
                    paths: ["serverstf/ui/styles/"]
                files:
                    "serverstf/ui/styles/serverstf.css":
                        "serverstf/ui/styles/serverstf.less"
        clean:
            coffee: ["serverstf/ui/scripts/*"]
            stylesheets: ["serverstf/ui/styles/*.css"]
        coffee:
            default:
                options:
                    sourceMap: true
                files: [
                    expand: true
                    cwd: "serverstf/ui/lib/"
                    src: ["**/*.coffee"]
                    dest: "serverstf/ui/scripts/"
                    ext: ".js"
                ]
    )
    grunt.loadNpmTasks("grunt-contrib-clean")
    grunt.loadNpmTasks("grunt-contrib-coffee")
    grunt.loadNpmTasks("grunt-contrib-less")
    grunt.loadNpmTasks("grunt-contrib-watch")
    grunt.registerTask("default", ["clean", "less", "coffee"])
