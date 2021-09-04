nav_div = document.getElementById("navigation-bar");

function addLink(name, href) {
	link_div = document.createElement("div");
	link = document.createElement("a");

	link_div.className = "navigation-link";
	nav_div.appendChild(link_div);

	link.text = name;
	link.href = href;

	link_div.appendChild(link);
}