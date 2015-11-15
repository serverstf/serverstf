module.exports = (grunt) ->
    grunt.initConfig(
        watch:
            stylesheets:
                files: ["serverstf/ui/styles/**/*.less"]
                tasks: ["clean:stylesheets", "less", "autoprefixer"]
            scripts:
                files: ["serverstf/ui/lib/**/*.coffee"]
                tasks: ["clean:coffee", "coffee", "bowerRequirejs"]
            maps:
                files: ["serverstf/ui/data/map*.yaml"]
                tasks: ["maps"]
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
        yaml:
            maps:
                options:
                    space: 0
                files:
                    "serverstf/ui/data/maps.schema.json":
                        "serverstf/ui/data/maps.schema.yaml"
                    "serverstf/ui/data/maps.json":
                        "serverstf/ui/data/maps.yaml"
                    "serverstf/ui/data/map-images.schema.json":
                        "serverstf/ui/data/map-images.schema.yaml"
                    "serverstf/ui/data/map-images.json":
                        "serverstf/ui/data/map-images.yaml"
        json_schema:
            maps:
                files:
                    "serverstf/ui/data/maps.schema.json":
                        "serverstf/ui/data/maps.json"
                    "serverstf/ui/data/map-images.schema.json":
                        "serverstf/ui/data/map-images.json"
        image_resize:
            master:
                options:
                    width: "100%"
                    height: "100%"
                files: [
                    expand: true
                    cwd: "serverstf/ui/images/maps/masters/"
                    src: ["**/*.jpg"]
                    dest: "serverstf/ui/images/maps/"
                    ext: "-master.jpg"
                ]
            350:
                options:
                    width: 350
                    height: 197
                files: [
                    expand: true
                    cwd: "serverstf/ui/images/maps/masters/"
                    src: ["**/*.jpg"]
                    dest: "serverstf/ui/images/maps/"
                    ext: "-350.jpg"
                ]
            900:
                options:
                    width: 900
                    height: 506
                files: [
                    expand: true
                    cwd: "serverstf/ui/images/maps/masters/"
                    src: ["**/*.jpg"]
                    dest: "serverstf/ui/images/maps/"
                    ext: "-900.jpg"
                ]
        shell:
            latency:
                command: "python -m serverstf latency-curve
                    serverstf/ui/data/latency.csv
                    --output serverstf/ui/data/latency-curve.json"
    )
    grunt.loadNpmTasks("grunt-autoprefixer")
    grunt.loadNpmTasks("grunt-bower-requirejs")
    grunt.loadNpmTasks("grunt-contrib-clean")
    grunt.loadNpmTasks("grunt-contrib-coffee")
    grunt.loadNpmTasks("grunt-contrib-less")
    grunt.loadNpmTasks("grunt-contrib-watch")
    grunt.loadNpmTasks("grunt-image-resize")
    grunt.loadNpmTasks("grunt-json-schema")
    grunt.loadNpmTasks("grunt-shell")
    grunt.loadNpmTasks("grunt-yaml")
    grunt.registerTask("requirejs-bower", [
        "clean:coffee",
        "coffee",
        "bowerRequirejs",
    ])
    grunt.registerTask("maps", [
        "yaml:maps",
        "json_schema:maps",
    ])
    grunt.registerTask("default", [
        "clean",
        "less",
        "autoprefixer",
        "coffee",
        "bowerRequirejs",
        "maps",
        "image_resize",
        "shell:latency",
    ])
