module.exports = (grunt) ->
    grunt.initConfig(
        watch:
            stylesheets:
                files: ["serverstf/ui/styles/**/*.less"]
                tasks: ["clean:stylesheets", "less", "autoprefixer"]
            scripts:
                files: ["serverstf/ui/lib/**/*.coffee"]
                tasks: ["clean:coffee", "coffee", "bowerRequirejs"]
        less:
            default:
                options:
                    paths: ["serverstf/ui/styles/"]
                files:
                    "serverstf/ui/styles/serverstf.css":
                        "serverstf/ui/styles/serverstf.less"
        autoprefixer:
            default:
                options:
                    browsers: ["last 2 versions"]
                    remove: true
                files:
                    "serverstf/ui/styles/serverstf.css":
                        "serverstf/ui/styles/serverstf.css"
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
        bowerRequirejs:
            target:
                rjsConfig: "serverstf/ui/scripts/config.js"
    )
    grunt.loadNpmTasks("grunt-autoprefixer")
    grunt.loadNpmTasks("grunt-bower-requirejs")
    grunt.loadNpmTasks("grunt-contrib-clean")
    grunt.loadNpmTasks("grunt-contrib-coffee")
    grunt.loadNpmTasks("grunt-contrib-less")
    grunt.loadNpmTasks("grunt-contrib-watch")
    grunt.registerTask("requirejs-bower", [
        "clean:coffee",
        "coffee",
        "bowerRequirejs",
    ])
    grunt.registerTask("default", [
        "clean",
        "less",
        "autoprefixer",
        "coffee",
        "bowerRequirejs",
    ])
