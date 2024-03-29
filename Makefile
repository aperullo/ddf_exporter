IMAGE_NAME=connexta/ddf_exporter
GIT_BRANCH:=$(shell git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,' 2>/dev/null)
ifneq ($(GIT_BRANCH), master)
	IMAGE_TAG=$(GIT_BRANCH)
else
	IMAGE_TAG=latest
endif

.PHONY: build
build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) -f Dockerfile .

.PHONY: deploy
deploy: build
	docker push $(IMAGE_NAME):$(IMAGE_TAG)