function modifyTableInfo(btn) {
    var tableID = Number(btn.getAttribute('table-id'))
    var table = document.getElementById('table-' + tableID)
    var info = table.getElementsByClassName('table-info')
    console.log(info)
}

