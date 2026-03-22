--
-- PostgreSQL database dump
--

\restrict 1yOnL7yjYvRVyVmM0o5SFbWBBIicIK25HDNnsFchugbDx6fmqf0pjauuV52JN0h

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: chat_histories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_histories (
    id integer NOT NULL,
    session_id character varying(255) NOT NULL,
    message jsonb NOT NULL
);


--
-- Name: chat_histories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_histories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chat_histories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_histories_id_seq OWNED BY public.chat_histories.id;


--
-- Name: user_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_events (
    id integer NOT NULL,
    chat_id bigint NOT NULL,
    event_type character varying(50) NOT NULL,
    event_data character varying(255) NOT NULL,
    language character varying(10),
    workflow_name character varying(100),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: user_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_events_id_seq OWNED BY public.user_events.id;


--
-- Name: users_nutrition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users_nutrition (
    chat_id bigint NOT NULL,
    username text,
    first_name text,
    sex character varying(10),
    age integer,
    weight numeric(5,2),
    height numeric(5,2),
    activity_level character varying(50),
    goal character varying(50),
    allergies text,
    excluded_foods text,
    calories integer,
    protein integer,
    fats integer,
    carbs integer,
    get_food boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    funnel_stage integer DEFAULT 0,
    funnel_start_at timestamp without time zone,
    last_funnel_msg_at timestamp without time zone,
    next_funnel_msg_at timestamp with time zone,
    is_buyer boolean DEFAULT false,
    language character varying(5) DEFAULT 'ru'::character varying,
    id_ziina text,
    type_ziina integer,
    CONSTRAINT users_nutrition_type_ziina_check CHECK ((type_ziina = ANY (ARRAY[49, 79, 99])))
);


--
-- Name: chat_histories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_histories ALTER COLUMN id SET DEFAULT nextval('public.chat_histories_id_seq'::regclass);


--
-- Name: user_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_events ALTER COLUMN id SET DEFAULT nextval('public.user_events_id_seq'::regclass);


--
-- Name: chat_histories chat_histories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_histories
    ADD CONSTRAINT chat_histories_pkey PRIMARY KEY (id);


--
-- Name: user_events user_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_events
    ADD CONSTRAINT user_events_pkey PRIMARY KEY (id);


--
-- Name: users_nutrition users_nutrition_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users_nutrition
    ADD CONSTRAINT users_nutrition_pkey PRIMARY KEY (chat_id);


--
-- Name: idx_clients_activity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_activity ON public.users_nutrition USING btree (activity_level);


--
-- Name: idx_clients_funnel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_funnel ON public.users_nutrition USING btree (funnel_stage);


--
-- Name: idx_clients_goal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_goal ON public.users_nutrition USING btree (goal);


--
-- Name: idx_clients_is_buyer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_is_buyer ON public.users_nutrition USING btree (is_buyer);


--
-- Name: idx_clients_sex; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_sex ON public.users_nutrition USING btree (sex);


--
-- Name: idx_clients_updated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_updated_at ON public.users_nutrition USING btree (updated_at DESC);


--
-- Name: idx_clients_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_username ON public.users_nutrition USING btree (username);


--
-- Name: idx_user_events_chat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_events_chat_id ON public.user_events USING btree (chat_id);


--
-- Name: idx_user_events_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_events_created_at ON public.user_events USING btree (created_at);


--
-- Name: idx_funnel_targets; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_funnel_targets ON public.users_nutrition USING btree (next_funnel_msg_at) WHERE ((get_food = true) AND ((is_buyer IS FALSE) OR (is_buyer IS NULL)) AND (funnel_stage >= 0));


--
-- Name: users_nutrition trg_clients_notify_del; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_clients_notify_del AFTER DELETE ON public.users_nutrition FOR EACH ROW EXECUTE FUNCTION public.notify_clients_changed();


--
-- Name: users_nutrition trg_clients_notify_ins; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_clients_notify_ins AFTER INSERT ON public.users_nutrition FOR EACH ROW EXECUTE FUNCTION public.notify_clients_changed();


--
-- Name: users_nutrition trg_clients_notify_upd; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_clients_notify_upd AFTER UPDATE ON public.users_nutrition FOR EACH ROW EXECUTE FUNCTION public.notify_clients_changed();


--
-- PostgreSQL database dump complete
--

\unrestrict 1yOnL7yjYvRVyVmM0o5SFbWBBIicIK25HDNnsFchugbDx6fmqf0pjauuV52JN0h

