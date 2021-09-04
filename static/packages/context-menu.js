function toggleMenuOn() {
	// показываем меню путем добавления contextMenuActive в его класс

	if ( menu.state != 1 ) {
		menu.state = 1;
		menu.element.classList.add(contextMenuActive);
	}
}

function toggleMenuOff() {
	if ( menu.state != 0 ) {
		menu.state = 0;
		menu.element.classList.remove(contextMenuActive);
	}
}

function getPosition(e) {
	var posx = 0;
	var posy = 0;

	if (!e)
		var e = window.event;

	if (e.pageX || e.pageY) {
		posx = e.pageX;
		posy = e.pageY;
	} else if (e.clientX || e.clientY) {
		posx = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
		posy = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
	}

	return {
		x: posx,
		y: posy
	}
}

function positionMenu(e) {
	// позиционирование меню относительно места клика

	let clickCoords = getPosition(e);
	let clickCoordsX = clickCoords.x;
	let clickCoordsY = clickCoords.y;

	let menuWidth = menu.element.offsetWidth + 4;
	let menuHeight = menu.element.offsetHeight + 4;

	let windowWidth = window.innerWidth;
	let windowHeight = window.innerHeight;

	if ( (windowWidth - clickCoordsX) < menuWidth ) {
		menu.element.style.left = windowWidth - menuWidth + "px";
	} else {
		menu.element.style.left = clickCoordsX + "px";
    }

    if ( (windowHeight - clickCoordsY) < menuHeight ) {
    	menu.element.style.top = windowHeight - menuHeight + "px";
    } else {
    	menu.element.style.top = clickCoordsY + "px";
    }
}