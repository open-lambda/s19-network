move_device() {
    location=$1
    data="{\"location\":$location}"
    curl -XPOST -d$data "http://23.0.0.3:9999/update_location"
}
