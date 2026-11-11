-- Эти функции и триггеры идут сверх обычного задания CREATE TABLE.
-- Выбор заявки блокирует строку проекта: два победителя одновременно невозможны.
CREATE FUNCTION choose_bid(bid_id bigint, decision_at timestamp DEFAULT CURRENT_TIMESTAMP::timestamp)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE p_id bigint; p_status text; b_status text;
BEGIN
 SELECT project_id INTO STRICT p_id FROM bids WHERE id=bid_id;
 SELECT status INTO p_status FROM projects WHERE id=p_id FOR UPDATE;
 SELECT status INTO b_status FROM bids WHERE id=bid_id;
 IF p_status <> 'открыт' OR b_status <> 'подана' THEN
   RAISE EXCEPTION 'Проект должен быть открыт, заявка — подана';
 END IF;
 IF decision_at < (SELECT max(submitted_at) FROM bids WHERE project_id=p_id) THEN
   RAISE EXCEPTION 'Решение не может предшествовать подаче заявок';
 END IF;
 UPDATE bids SET status='отклонена', rejected_at=decision_at WHERE project_id=p_id AND id<>bid_id AND status='подана';
 UPDATE bids SET status='принята', accepted_at=decision_at WHERE id=bid_id;
 UPDATE projects SET status='в работе' WHERE id=p_id;
END $$;
CREATE FUNCTION complete_project(p_id bigint, finished_at timestamp DEFAULT CURRENT_TIMESTAMP::timestamp)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 PERFORM 1 FROM projects WHERE id=p_id AND status='в работе' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Проект должен быть в работе'; END IF;
 IF finished_at < (SELECT accepted_at FROM bids WHERE project_id=p_id AND status='принята') THEN
   RAISE EXCEPTION 'Завершение раньше принятия';
 END IF;
 UPDATE projects SET status='завершен', completed_at=finished_at WHERE id=p_id;
END $$;
CREATE FUNCTION validate_project_state() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p_id bigint; p_status text; done timestamp; n integer; affected bigint[];
BEGIN
 IF TG_TABLE_NAME='projects' THEN affected:=ARRAY[NEW.id,OLD.id];
 ELSE affected:=ARRAY[NEW.project_id,OLD.project_id]; END IF;
 FOREACH p_id IN ARRAY affected LOOP
 IF p_id IS NULL THEN CONTINUE; END IF;
 SELECT status,completed_at INTO p_status,done FROM projects WHERE id=p_id;
 IF NOT FOUND THEN CONTINUE; END IF;
 SELECT count(*) INTO n FROM bids WHERE project_id=p_id AND status='принята';
 IF (p_status='открыт' AND n<>0) OR (p_status<>'открыт' AND n<>1) THEN
   RAISE EXCEPTION 'Число принятых заявок не соответствует статусу проекта %',p_id;
 END IF;
 IF p_status<>'открыт' AND EXISTS(SELECT 1 FROM bids WHERE project_id=p_id AND status='подана') THEN
   RAISE EXCEPTION 'У выбранного исполнителя остальные заявки должны быть отклонены';
 END IF;
 IF EXISTS(SELECT 1 FROM bids b JOIN projects p ON p.id=b.project_id WHERE p.id=p_id AND
   (b.submitted_at<p.created_at OR (done IS NOT NULL AND b.accepted_at>done))) THEN
   RAISE EXCEPTION 'Нарушена хронология проекта';
 END IF;
 IF EXISTS(SELECT 1 FROM reviews WHERE project_id=p_id AND (p_status<>'завершен' OR created_at<done)) THEN
   RAISE EXCEPTION 'Отзыв разрешен только после завершения';
 END IF;
 END LOOP;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER project_integrity AFTER INSERT OR UPDATE OR DELETE ON projects
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_project_state();
CREATE CONSTRAINT TRIGGER bid_integrity AFTER INSERT OR UPDATE OR DELETE ON bids
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_project_state();
CREATE CONSTRAINT TRIGGER review_integrity AFTER INSERT OR UPDATE OR DELETE ON reviews
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_project_state();
