 function isValidJson(json) {
    try {
        JSON.parse(json);
        return true;
    } catch (e) {
        return false;
    }
}