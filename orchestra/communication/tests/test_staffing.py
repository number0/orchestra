from orchestra.bots.errors import StaffingResponseException
from orchestra.communication.staffing import handle_staffing_response
from orchestra.models import StaffingResponse
from orchestra.models import TaskAssignment
from orchestra.tests.helpers import OrchestraTestCase
from orchestra.tests.helpers.fixtures import StaffingRequestInquiryFactory
from orchestra.tests.helpers.fixtures import WorkerFactory


class StaffingTestCase(OrchestraTestCase):

    def setUp(self):
        self.worker = WorkerFactory()
        self.staffing_request_inquiry = StaffingRequestInquiryFactory(
            communication_preference__worker=self.worker,
            request__task__step__is_human=True
        )
        super().setUp()

    def test_handle_staffing_response_invalid_request(self):
        old_count = StaffingResponse.objects.all().count()

        # Invalid staffing_request_inquiry_id
        response = handle_staffing_response(
            self.worker, None, is_available=True)
        self.assertEqual(response, None)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count)

        # Invalid worker
        response = handle_staffing_response(
            None, self.staffing_request_inquiry.id, is_available=True)
        self.assertEqual(response, None)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count)

    def test_handle_staffing_response_is_available(self):
        # Test StaffingResponse object creation
        old_count = StaffingResponse.objects.all().count()
        response = handle_staffing_response(
            self.worker, self.staffing_request_inquiry.id,
            is_available=True)
        self.assertTrue(response.is_winner)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count + 1)

        task_assignment = (
            TaskAssignment.objects
            .get(worker=self.worker,
                 task=self.staffing_request_inquiry.request.task))
        self.assertEquals(task_assignment.status,
                          TaskAssignment.Status.PROCESSING)
        self.staffing_request_inquiry.request.task.refresh_from_db()

        # Replay of same request
        response = handle_staffing_response(
            self.worker, self.staffing_request_inquiry.id, is_available=True)
        self.assertTrue(response.is_winner)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count + 1)

        # Change mind to `is_available=False` does not do anything
        with self.assertRaises(StaffingResponseException):
            response = handle_staffing_response(
                self.worker, self.staffing_request_inquiry.id,
                is_available=False)

        new_request_inquiry = StaffingRequestInquiryFactory(
            request__task__step__is_human=True
        )
        new_worker = new_request_inquiry.communication_preference.worker
        old_count = StaffingResponse.objects.all().count()
        response = handle_staffing_response(
            new_worker, new_request_inquiry.id, is_available=True)
        self.assertTrue(response.is_winner)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count + 1)

    def test_handle_staffing_response_not_is_available(self):
        # Test StaffingResponse object creation
        old_count = StaffingResponse.objects.all().count()
        response = handle_staffing_response(
            self.worker, self.staffing_request_inquiry.id,
            is_available=False)
        self.assertFalse(response.is_winner)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count + 1)

        # Replay of same request
        response = handle_staffing_response(
            self.worker, self.staffing_request_inquiry.id,
            is_available=False)
        self.assertFalse(response.is_winner)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count + 1)

        # Change mind to `is_available=True`
        response = handle_staffing_response(
            self.worker, self.staffing_request_inquiry.id,
            is_available=True)
        self.assertTrue(response.is_winner)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count + 1)

        # Task is not available to claim
        new_request_inquiry = StaffingRequestInquiryFactory(
            request=self.staffing_request_inquiry.request,
            request__task__step__is_human=True)
        new_worker = new_request_inquiry.communication_preference.worker
        old_count = StaffingResponse.objects.all().count()
        response = handle_staffing_response(
            new_worker, new_request_inquiry.id, is_available=True)
        self.assertFalse(response.is_winner)
        self.assertEqual(StaffingResponse.objects.all().count(), old_count + 1)
