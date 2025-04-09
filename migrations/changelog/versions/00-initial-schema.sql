CREATE TABLE IF NOT EXISTS users (
    chat_id BIGINT PRIMARY KEY,
    username VARCHAR(100) NULL
);

CREATE TABLE IF NOT EXISTS tracked_links (
    link_id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    url VARCHAR(255) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE, 
    filters VARCHAR(255),
    CONSTRAINT fk_user FOREIGN KEY (chat_id) REFERENCES users (chat_id) ON DELETE CASCADE,
    CONSTRAINT unique_chat_url UNIQUE (chat_id, url)
);

CREATE TABLE IF NOT EXISTS tags (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL CONSTRAINT unique_tag_name UNIQUE
);

CREATE TABLE IF NOT EXISTS links_tags (
    link_id INT NOT NULL,
    tag_id INT NOT NULL,
    FOREIGN KEY (link_id) REFERENCES tracked_links (link_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (tag_id) ON DELETE CASCADE,
    PRIMARY KEY (link_id, tag_id)
);

CREATE TABLE IF NOT EXISTS link_mute_statuses (
    mute_status_id SERIAL PRIMARY KEY,
    link_id INT NOT NULL,
    chat_id BIGINT NOT NULL,
    muted BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (link_id) REFERENCES tracked_links (link_id) ON DELETE CASCADE,
    CONSTRAINT unique_link_chat UNIQUE (link_id, chat_id)
);

CREATE INDEX idx_tracked_links_last_updated ON tracked_links (last_updated);

CREATE INDEX idx_tracked_links_chat_id ON tracked_links (chat_id);

CREATE INDEX idx_users_chat_id ON users (chat_id);

CREATE INDEX idx_links_tags_link_id ON links_tags (link_id);

CREATE INDEX idx_links_tags_tag_id ON links_tags (tag_id);

CREATE INDEX idx_link_mute_statuses_link_id ON link_mute_statuses (link_id);