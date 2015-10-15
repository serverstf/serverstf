# This is the base RequireJS config. Bower-provided modules will be merged
# into the `paths` option by the `bowerRequirejs` Grunt task.

require.config(
    shim:
        angular:
            exports: "angular"
    paths: {}
    packages: []
)
