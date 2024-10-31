run:
	docker run -it -d --restart=unless-stopped --name refer bot_image
stop:
	docker stop refer
attach:
	docker attach refer
dell:
	docker rm refer
