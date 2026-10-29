class ApplicationController < ActionController::Base
  protect_from_forgery with: :null_session
  before_action :authenticate!

  private

  def authenticate!
    @current_user = User.find_by(api_token: request.headers["X-Api-Token"])
    head :unauthorized unless @current_user
  end

  attr_reader :current_user
end
