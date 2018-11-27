# -*- coding: utf-8 -*-

import openeo
from unittest import TestCase
import tempfile
import os
import json

import requests_mock

# MockUp Testdata

CAPABILITIES = ['/capabilities', '/capabilities/services', '/capabilities/output_formats', '/data',
                '/data/{product_id}', '/processes']
COLLECTIONS = [{'product_id': 'ASTER/AST_L1T_003',
  'description': 'ASTER L1T Radiance',
  'source': 'NASA LP DAAC at the USGS EROS Center, https://lpdaac.usgs.gov/dataset_discovery/aster/aster_products_table/ast_l1t'},
 {'product_id': 'AU/GA/AUSTRALIA_5M_DEM',
  'description': 'Australian 5M DEM',
  'source': 'Geoscience Australia, https://ecat.ga.gov.au/geonetwork/srv/eng/search#!22be4b55-2465-4320-e053-10a3070a5236'},
 {'product_id': 'COPERNICUS/S2',
 'description': 'Sentinel-2 MSI: MultiSpectral Instrument, Level-1C',
 'source': 'European Union/ESA/Copernicus, https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi',
 'time': {'from': '2015-06-23', 'to': '2018-06-27'},
 'bands': [{'band_id': 'B1'},
  {'band_id': 'B2'},
  {'band_id': 'B3'},
  {'band_id': 'B4'},
  {'band_id': 'B5'},
  {'band_id': 'B6'},
  {'band_id': 'B7'},
  {'band_id': 'B8'},
  {'band_id': 'B8A'},
  {'band_id': 'B9'},
  {'band_id': 'B10'},
  {'band_id': 'B11'},
  {'band_id': 'B12'},
  {'band_id': 'QA10'},
  {'band_id': 'QA20'},
  {'band_id': 'QA60'}],
 'extent': {'srs': 'EPSG:4326',
  'left': -180,
  'right': 180,
  'bottom': -90,
  'top': 90}}]

PROCESSES = [{'process_id': 'zonal_statistics',
  'description': 'Calculates statistics for each zone specified in a file.'},
 {'process_id': 'NDVI',
  'description': 'Finds the minimum value of time series for all bands of the input dataset.'},
 {'process_id': 'filter_bands',
  'description': 'Selects certain bands from a collection.'}]


@requests_mock.mock()
class TestUserFiles(TestCase):

    def setUp(self):
        # configuration phase: define username, endpoint, parameters?
        self.endpoint = "http://localhost:8000/api"
        self.user_id = "174367998144"
        self.auth_id = "test"
        self.auth_pwd = "test"
        self.upload_remote_fname = 'polygon.json'
        self.upload_local_fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               'polygon.json')

    def match_uploaded_file(self, request):

        with open(self.upload_local_fname, 'r') as uploaded_file:
            content = uploaded_file.read()
        assert request.json() == json.loads(content)
        return True

    def match_process_graph(self, request):

        assert request.json() == PROCESSES
        return True

    def test_user_upload_file(self, m):
        upload_url = "{}/files/{}/{}".format(self.endpoint, self.user_id, self.upload_remote_fname)
        m.register_uri('PUT', upload_url, additional_matcher=self.match_uploaded_file)
        session = openeo.session(self.user_id, endpoint=self.endpoint)
        session.auth(self.auth_id, self.auth_pwd)
        status = session.user_upload_file(self.upload_local_fname,
                                          remote_path=self.upload_remote_fname)
        assert status

    def test_user_download_file(self, m):
        download_url = "{}/users/{}/files/{}".format(self.endpoint, self.user_id, self.upload_remote_fname)
        with open(self.upload_local_fname, 'rb') as response_file:
            content = response_file.read()
        m.get(download_url, content=content)
        session = openeo.session(self.user_id, endpoint=self.endpoint)
        session.auth(self.auth_id, self.auth_pwd)
        local_output_fd, local_output_fname = tempfile.mkstemp()
        try:
            status = session.user_download_file(self.upload_remote_fname,
                                                local_output_fname)
            assert status
            with open(local_output_fname, 'rb') as downloaded_file:
                downloaded_content = downloaded_file.read()
        finally:
            os.close(local_output_fd)
            os.remove(local_output_fname)

        assert content == downloaded_content

    def test_user_delete_file(self, m):
        delete_url = "{}/users/{}/files/{}".format(self.endpoint, self.user_id,
                                                                         self.upload_remote_fname)
        m.register_uri('DELETE', delete_url)
        session = openeo.session(self.user_id, endpoint=self.endpoint)
        session.auth(self.auth_id, self.auth_pwd)
        status = session.user_delete_file(self.upload_remote_fname)
        assert status

    def test_list_capabilities(self, m):
        capabilties_url = "{}/capabilities".format(self.endpoint)
        m.register_uri('GET', capabilties_url, json=CAPABILITIES)
        session = openeo.session(self.user_id, endpoint=self.endpoint)

        capabilities = session.list_capabilities()
        assert capabilities == CAPABILITIES

    def test_list_collections(self, m):
        collection_url = "{}/data".format(self.endpoint)
        m.register_uri('GET', collection_url, json=COLLECTIONS)
        session = openeo.session(self.user_id, endpoint=self.endpoint)

        collections = session.list_collections()
        assert collections == COLLECTIONS

    def test_get_collection(self, m):
        collection_org = COLLECTIONS[0]
        collection_id = collection_org["product_id"]
        collection_url = "{}/data/{}".format(self.endpoint, collection_id)
        m.register_uri('GET', collection_url, json=collection_org)
        session = openeo.session(self.user_id, endpoint=self.endpoint)

        collection = session.get_collection(collection_id)
        assert collection == collection_org

    def test_get_all_processes(self, m):
        processes_url = "{}/processes".format(self.endpoint)
        m.register_uri('GET', processes_url, json=PROCESSES)
        session = openeo.session(self.user_id, endpoint=self.endpoint)

        processes = session.get_all_processes()
        assert processes == PROCESSES

    def test_get_process(self, m):
        process_org = PROCESSES[0]
        process_id = process_org['process_id']
        process_url = "{}/processes/{}".format(self.endpoint, process_id)
        m.register_uri('GET', process_url, json=process_org)
        session = openeo.session(self.user_id, endpoint=self.endpoint)

        process = session.get_process(process_id)
        assert process == process_org

    def test_create_job(self, m):

        post_data = PROCESSES
        job_id = "MyId"
        result = {"job_id": job_id}

        m.register_uri('POST', "{}/jobs?evaluate={}".format(self.endpoint, "lazy"), status_code=200, json=result, additional_matcher=self.match_process_graph)
        m.register_uri('POST', "{}/jobs?evaluate={}".format(self.endpoint, "wrong"), status_code=400, additional_matcher=self.match_process_graph)

        session = openeo.session(self.user_id, endpoint=self.endpoint)

        resp = session.create_job(post_data)

        assert resp == job_id

        resp = session.create_job(post_data, evaluation="wrong")

        assert resp is None

    def test_image(self, m):

        collection_org = COLLECTIONS[2]
        collection_id = collection_org["product_id"]
        collection_url = "{}/data/{}".format(self.endpoint, collection_id)
        m.register_uri('GET', collection_url, json=collection_org)

        session = openeo.session(self.user_id, endpoint=self.endpoint)

        resp = session.image(collection_id)

        assert resp.bands == ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
                             'B8A', 'B9', 'B10', 'B11', 'B12', 'QA10', 'QA20', 'QA60']

    def user_jobs(self, m):

        collection_url = "{}/users/{}/jobs".format(self.endpoint, self.user_id)
        m.register_uri('GET', collection_url, json=PROCESSES)

        session = openeo.session(self.user_id, endpoint=self.endpoint)

        resp = session.user_jobs()

        assert resp == PROCESSES
