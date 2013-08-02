--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: edges; Type: TABLE; Schema: public; Owner: next; Tablespace: 
--

CREATE TABLE edges (
    id integer NOT NULL,
    from_node_id integer,
    to_node_id integer,
    scenario_id integer,
    distance integer,
    phase_id integer
);


ALTER TABLE public.edges OWNER TO next;

--
-- Name: edges_id_seq; Type: SEQUENCE; Schema: public; Owner: next
--

CREATE SEQUENCE edges_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.edges_id_seq OWNER TO next;

--
-- Name: edges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: next
--

ALTER SEQUENCE edges_id_seq OWNED BY edges.id;


--
-- Name: nodes; Type: TABLE; Schema: public; Owner: next; Tablespace: 
--

CREATE TABLE nodes (
    id integer NOT NULL,
    weight integer,
    node_type_id integer,
    scenario_id integer,
    point geometry(Point,4326),
    phase_id integer
);


ALTER TABLE public.nodes OWNER TO next;

--
-- Name: phase_ancestors; Type: TABLE; Schema: public; Owner: next; Tablespace: 
-- This table is a denormalization that helps map to the object model
--

CREATE TABLE phase_ancestors (
    id integer NOT NULL,
    phase_id integer,
    ancestor_phase_id integer,
    scenario_id integer NOT NULL
);


ALTER TABLE public.phase_ancestors OWNER TO next;

--
-- Name: nodes_id_seq; Type: SEQUENCE; Schema: public; Owner: next
--

CREATE SEQUENCE nodes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.nodes_id_seq OWNER TO next;

--
-- Name: nodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: next
--

ALTER SEQUENCE nodes_id_seq OWNED BY nodes.id;


--
-- Name: nodetypes; Type: TABLE; Schema: public; Owner: next; Tablespace: 
--

CREATE TABLE nodetypes (
    id integer NOT NULL,
    name character varying
);


ALTER TABLE public.nodetypes OWNER TO next;

--
-- Name: nodetypes_id_seq; Type: SEQUENCE; Schema: public; Owner: next
--

CREATE SEQUENCE nodetypes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.nodetypes_id_seq OWNER TO next;

--
-- Name: nodetypes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: next
--

ALTER SEQUENCE nodetypes_id_seq OWNED BY nodetypes.id;


--
-- Name: phase_ancestors_id_seq; Type: SEQUENCE; Schema: public; Owner: next
--

CREATE SEQUENCE phase_ancestors_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.phase_ancestors_id_seq OWNER TO next;

--
-- Name: phase_ancestors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: next
--

ALTER SEQUENCE phase_ancestors_id_seq OWNED BY phase_ancestors.id;


--
-- Name: phases; Type: TABLE; Schema: public; Owner: next; Tablespace: 
--

CREATE TABLE phases (
    id integer NOT NULL,
    scenario_id integer NOT NULL,
    parent_id integer,
    name character varying
);


ALTER TABLE public.phases OWNER TO next;

--
-- Name: scenarios; Type: TABLE; Schema: public; Owner: next; Tablespace: 
--

CREATE TABLE scenarios (
    id integer NOT NULL,
    name character varying
);


ALTER TABLE public.scenarios OWNER TO next;

--
-- Name: scenarios_id_seq; Type: SEQUENCE; Schema: public; Owner: next
--

CREATE SEQUENCE scenarios_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scenarios_id_seq OWNER TO next;

--
-- Name: scenarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: next
--

ALTER SEQUENCE scenarios_id_seq OWNED BY scenarios.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: next
--

ALTER TABLE edges ALTER COLUMN id SET DEFAULT nextval('edges_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: next
--

ALTER TABLE nodes ALTER COLUMN id SET DEFAULT nextval('nodes_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: next
--

ALTER TABLE nodetypes ALTER COLUMN id SET DEFAULT nextval('nodetypes_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: next
--

ALTER TABLE phase_ancestors ALTER COLUMN id SET DEFAULT nextval('phase_ancestors_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: next
--

ALTER TABLE scenarios ALTER COLUMN id SET DEFAULT nextval('scenarios_id_seq'::regclass);


--
-- Name: edges_pkey; Type: CONSTRAINT; Schema: public; Owner: next; Tablespace: 
--

ALTER TABLE ONLY edges
    ADD CONSTRAINT edges_pkey PRIMARY KEY (id);


--
-- Name: nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: next; Tablespace: 
--

ALTER TABLE ONLY nodes
    ADD CONSTRAINT nodes_pkey PRIMARY KEY (id);


--
-- Name: nodetypes_pkey; Type: CONSTRAINT; Schema: public; Owner: next; Tablespace: 
--

ALTER TABLE ONLY nodetypes
    ADD CONSTRAINT nodetypes_pkey PRIMARY KEY (id);


--
-- Name: phase_ancestors_pkey; Type: CONSTRAINT; Schema: public; Owner: next; Tablespace: 
--

ALTER TABLE ONLY phase_ancestors
    ADD CONSTRAINT phase_ancestors_pkey PRIMARY KEY (id);


--
-- Name: phases_pkey; Type: CONSTRAINT; Schema: public; Owner: next; Tablespace: 
--

ALTER TABLE ONLY phases
    ADD CONSTRAINT phases_pkey PRIMARY KEY (id, scenario_id);


--
-- Name: scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: next; Tablespace: 
--

ALTER TABLE ONLY scenarios
    ADD CONSTRAINT scenarios_pkey PRIMARY KEY (id);


--
-- Name: idx_nodes_point; Type: INDEX; Schema: public; Owner: next; Tablespace: 
--

CREATE INDEX idx_nodes_point ON nodes USING gist (point);


--
-- Name: edges_from_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY edges
    ADD CONSTRAINT edges_from_node_id_fkey FOREIGN KEY (from_node_id) REFERENCES nodes(id);


--
-- Name: edges_phase_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY edges
    ADD CONSTRAINT edges_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);


--
-- Name: edges_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY edges
    ADD CONSTRAINT edges_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES scenarios(id);


--
-- Name: edges_to_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY edges
    ADD CONSTRAINT edges_to_node_id_fkey FOREIGN KEY (to_node_id) REFERENCES nodes(id);


--
-- Name: nodes_node_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY nodes
    ADD CONSTRAINT nodes_node_type_id_fkey FOREIGN KEY (node_type_id) REFERENCES nodetypes(id);


--
-- Name: nodes_phase_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY nodes
    ADD CONSTRAINT nodes_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);


--
-- Name: nodes_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY nodes
    ADD CONSTRAINT nodes_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES scenarios(id);


--
-- Name: phase_ancestors_ancestor_phase_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY phase_ancestors
    ADD CONSTRAINT phase_ancestors_ancestor_phase_fkey FOREIGN KEY (ancestor_phase_id, scenario_id) REFERENCES phases(id, scenario_id);


--
-- Name: phase_ancestors_phase_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY phase_ancestors
    ADD CONSTRAINT phase_ancestors_phase_fkey FOREIGN KEY (phase_id, scenario_id) REFERENCES phases(id, scenario_id);


--
-- Name: phase_ancestors_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY phase_ancestors
    ADD CONSTRAINT phase_ancestors_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES scenarios(id);


--
-- Name: phases_parent_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY phases
    ADD CONSTRAINT phases_parent_fkey FOREIGN KEY (parent_id, scenario_id) REFERENCES phases(id, scenario_id);


--
-- Name: phases_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: next
--

ALTER TABLE ONLY phases
    ADD CONSTRAINT phases_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES scenarios(id);


--
-- PostgreSQL database dump complete
--

